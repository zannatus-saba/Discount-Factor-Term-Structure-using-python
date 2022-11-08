
#-----------------------------------------------------------------------------#
#Reads in the relevant packages.
#-----------------------------------------------------------------------------#

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import dateutil
import bs4 as bs
import requests
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

#----------------------------------------------------------------------------#
#Reads in the treasuries data table and formats it.
#----------------------------------------------------------------------------#

f1='C:/Users/zanna/.spyder-py3/derivatives/bills2021-09-15.txt'
f2='C:/Users/zanna/.spyder-py3/derivatives/bonds2021-09-15.txt'
#url="http://www.wsj.com/mdc/public/page/2_3020-treasury.html" (old)
#data=pd.read_html(url) #Reads in the data tables. (old)
bills=pd.read_csv(f1,sep='\t') #Selects the Treasury Bills table.
bonds=pd.read_csv(f2,sep='\t') #Selects the Treasury Notes/Bonds table.
bills=bills.rename(columns={'MATURITY':'Maturity','BID':'Bid','ASKED':'Asked','CHG':'Chg',
                            'ASKED YIELD':'Askedyield'})
bonds=bonds.rename(columns={'MATURITY':'Maturity','COUPON':'Coupon','BID':'Bid',
                            'ASKED':'Asked','CHG':'Chg','ASKED YIELD':'Askedyield'})
#drops the rows where the bond or bill price has n.a.
i=0
count=0
while i<len(bills):
    if(bills.Asked[i]=='n.a.' or bills.Asked[i]=='n.a'):
        count=count+1
        if count>0:
            i=len(bills)
    i=i+1
if(count>0):
    bills.drop(bills.index[bills.loc[bills.Asked=='n.a.'].index], inplace=True)
    bills.drop(bills.index[bills.loc[bills.Asked=='n.a'].index], inplace=True)
i=0
count=0
while i<len(bonds):
    if(bonds.Asked[i]=='n.a.' or bonds.Asked[i]=='n.a'):
        count=count+1
        if count>0:
            i=len(bonds)
    i=i+1
if(count>0):
    bonds.drop(bonds.index[bonds.loc[bonds.Asked=='n.a.'].index], inplace=True)
    bonds.drop(bonds.index[bonds.loc[bonds.Asked=='n.a'].index], inplace=True)
#Adjusts the bond price since the new data has the decimal as the fraction of 32.
bonds.Asked=divmod(pd.to_numeric(bonds.Asked),1)[0]+divmod(pd.to_numeric(bonds.Asked),1)[1]*100/32
#bills.columns=bills.iloc[0] #Renames the bills header to be the names in row 0. (old)
#bonds.columns=bonds.iloc[0] #Renames the bonds header to be the names in row 0. (old)
#drops the redundant header in row 0.
#bills=bills.drop([0]) (old)
#bonds=bonds.drop([0]) (old)
#Identifies today's date.
#f = requests.get(url) #Reads in the url info (old)
#soup=bs.BeautifulSoup(f.text,'html.parser') #parses the url into text (old)
#l=soup.find("div",{"class":"tbltime"}) #Finds the location of the table date (old)
#for span in l.findAll('span'): #Keeps only the last obs in this class, which is the date (old)
#    date=span.text (old)
#dt=parse(date) #Converts the date format. (old)
dt=f1[len(f1)-14:len(f1)-4]
#today=pd.to_datetime(dt.strftime('%Y-%m-%d')) #Makes the date a datetime variable in the format we want. (old)
today=pd.to_datetime(dt)
#bills.to_csv("bills"+str(today.date())+".csv")  #Saves bills data to csv on computer
#bonds.to_csv("bonds"+str(today.date())+".csv") #Saves bonds data to csv on computer
yrlen=365 #The number of days assumed to be in 1 year.
#converts bonds and bills maturity dates to datetime values.
bonds.Maturity=pd.to_datetime(bonds.Maturity)
bills.Maturity=pd.to_datetime(bills.Maturity)
#Converts bonds and bills asked yields to numeric values
bonds.Askedyield=pd.to_numeric(bonds.Askedyield)
bills.Askedyield=pd.to_numeric(bills.Askedyield)
#Keeps only bonds from the bonds table with a maturity of >1-year from today.
bonds=bonds[(bonds.Maturity-datetime.timedelta(yrlen))>today]
 #Keeps only the first maturity date, when there are multiple obs with the same
 #maturity date.
bonds=bonds[bonds.Maturity != bonds.Maturity.shift(1)]
bills=bills[bills.Maturity != bills.Maturity.shift(1)]
bonds.index=np.arange(1,len(bonds)+1) #Resets the new obs. index to start with 1.
bills.index=np.arange(1,len(bills)+1) #Resets the new obs. index to start with 1.
#Calculates the time-to-maturity in years
bills['Ttm']=pd.to_numeric((bills.Maturity-today)/datetime.timedelta(yrlen))
bonds['Ttm']=pd.to_numeric((bonds.Maturity-today)/datetime.timedelta(yrlen))
bills['Price']=1./(1.+(bills.Askedyield/100)*bills.Ttm) #Treasury bill prices.

#-----------------------------------------------------------------------------#
#Bootstraps the zero-curve for bonds observations. Semi-annual coupon payments
#is used with the coupon payments on
#-----------------------------------------------------------------------------#

#Sets the ask price for the coupon bond, which all the coupons will be stripped
#from to attain the final zero price as the result.
bonds['ZeroPrice']=pd.to_numeric(bonds.Asked)/100 #sets the quoted price
bonds.Coupon=pd.to_numeric(bonds.Coupon) #Makes the coupons a numeric vlaue.
i=1 #Sets the bond index counting variable to the first obs.
while i<=len(bonds): #Iterates over all the bonds
    
    #Strips the coupons from the quoted bond Asks.
    s=np.floor(pd.to_numeric((bonds.Maturity[i]-today)/datetime.timedelta(yrlen))*2)
    while ((bonds.Maturity[i]-dateutil.relativedelta.relativedelta(months=s*6)>today) & (bonds.Maturity[i]-dateutil.relativedelta.relativedelta(months=s*6)<bonds.Maturity[i])):
        #Calculates the coupon date.
        cpndate=bonds.Maturity[i]-dateutil.relativedelta.relativedelta(months=s*6)
        #calculates the absolute difference between the coupon date and all 
        #available zero-coupon bills maturity dates.
        if pd.to_numeric((cpndate-today)/datetime.timedelta(yrlen))<1:
            absdif=abs(bills.Maturity-cpndate)
            df=bills.Price[absdif.idxmin()]
        else:
            absdif=abs(bonds.Maturity-cpndate)
            df=bonds.ZeroPrice[absdif.idxmin()]
        #Strips the coupon, using the bill with the closest maturity date to
        #the coupon date
        if s==np.floor(pd.to_numeric((bonds.Maturity[i]-today)/datetime.timedelta(yrlen))*2):
            #Adds accrued interest to the published "clean" price.
            bonds.ZeroPrice[i]=bonds.ZeroPrice[i]+((bonds.Coupon[i]/100)/2)*(1-pd.to_numeric((cpndate-today)/datetime.timedelta(30*6)))
        bonds.ZeroPrice[i]=bonds.ZeroPrice[i]-((bonds.Coupon[i]/100)/2)*df
        s=s-1
    bonds.ZeroPrice[i]=bonds.ZeroPrice[i]/(1+((bonds.Coupon[i]/100)/2))
    #This if statement corrects for numerical errors resulting in large jumps
    #in the zerio yield.
    if i>1 and (bonds.ZeroPrice[i]/bonds.ZeroPrice[i-1]-1)>0.01:
        bonds.ZeroPrice[i]=1/((1+1/(bonds.ZeroPrice[i-1]**(1/bonds.Ttm[i-1]))-1)**bonds.Ttm[i])
    i=i+1
#Calculates the yield implied by the coupon bond's bootstrapped zero-coupon
#price.
bonds['ZeroYield']=(1/(bonds.ZeroPrice**(1/bonds.Ttm))-1)*100

#-----------------------------------------------------------------------------#
#Appends the term-structure (using coupon bonds).
#-----------------------------------------------------------------------------#
term=pd.DataFrame((bills.Askedyield).append(bonds.Askedyield))
term['Maturity']=(bills.Maturity).append(bonds.Maturity)
term.index=np.arange(1,len(term)+1)

#-----------------------------------------------------------------------------#
#Appends the zero curves
#-----------------------------------------------------------------------------#

zeros=pd.DataFrame((bills.Askedyield).append(bonds.ZeroYield))
zeros.columns=['Yield']
zeros['Price']=(bills.Price).append(bonds.ZeroPrice)
zeros['Maturity']=(bills.Maturity).append(bonds.Maturity)
zeros.index=np.arange(1,len(zeros)+1)
#Constructs a 12-month rolling centered moving average of yields.
zeros['MA']=zeros.Yield.rolling(window=12,center=True,min_periods=0).mean()

#-----------------------------------------------------------------------------#
#Plots the bills zero-curve
#-----------------------------------------------------------------------------#

plt.plot(term.Maturity,term.Askedyield,color='blue')
plt.plot(zeros.Maturity,zeros.Yield,color="red")
plt.ylim(0.,4.)
plt.title("Yield curve"+" ("+str(today.date())+")")
plt.xlabel("Maturity date")
plt.ylabel("Interest rate")
plt.gca().legend(('coupon','bootstrapped zero'),loc='lower right')
plt.show()

plt.plot(bills.Maturity[1:len(bills)],bills.Price[1:len(bills)],
        bonds.Maturity[1:len(bonds)],bonds.ZeroPrice[1:len(bonds)],
        color="black")
plt.title("Term structure of discount factors"+" ("+str(today.date())+")")
plt.xlabel("Maturity date")
plt.ylabel("Discount factor")
plt.show()

#-----------------------------------------------------------------------------#
#Forward curve. F(t;T,T+3 months)
#Linearly interpolated
#-----------------------------------------------------------------------------#
zeros["Fwrd"]=zeros.Yield
i=1
while(i<=len(zeros)-1):
    ft=zeros.Maturity[i]
    fs=zeros.Maturity[i]+dateutil.relativedelta.relativedelta(months=3)
    tau=pd.to_numeric((fs-ft)/datetime.timedelta(yrlen))
    dif=pd.to_numeric(zeros.Maturity-fs)
    absdifs=abs(zeros.Maturity-fs)
    sgn=np.sign(dif[absdifs.idxmin()])
    if sgn==-1:
        ps=zeros.Price[absdifs.idxmin()]+(fs-zeros.Maturity[absdifs.idxmin()])/(zeros.Maturity[absdifs.idxmin()+1]-zeros.Maturity[absdifs.idxmin()])*(zeros.Price[absdifs.idxmin()+1]-zeros.Price[absdifs.idxmin()])
    if sgn==1:
        ps=zeros.Price[absdifs.idxmin()-1]+(fs-zeros.Maturity[absdifs.idxmin()-1])/(zeros.Maturity[absdifs.idxmin()]-zeros.Maturity[absdifs.idxmin()-1])*(zeros.Price[absdifs.idxmin()]-zeros.Price[absdifs.idxmin()-1])
    if sgn==0:
        ps=zeros.Price[absdifs.idxmin()]
    zeros.Fwrd[i]=(1/tau)*(zeros.Price[i]/ps-1)*100
    if i==len(zeros)-1:
        zeros.Fwrd[i+1]=zeros.Fwrd[i]
    i=i+1

zeros['FwrdMA']=zeros.Fwrd.rolling(window=6,center=True,min_periods=0).mean() #Rolling centered moving average
zeros['Ttm']=pd.to_numeric((zeros.Maturity-today)/datetime.timedelta(yrlen)) #Time to maturity in years
PlyFit=np.polyfit(zeros.Ttm,zeros.Fwrd,9) #Polynomial deg(9) fit to TTM.
zeros['PlyFit']=np.polyval(PlyFit,zeros.Ttm)

plt.plot(term.Maturity,term.Askedyield,color='blue')
plt.plot(zeros.Maturity,zeros.Yield,color="red")
plt.plot(zeros.Maturity,np.polyval(PlyFit,zeros.Ttm),color="green")
plt.plot(zeros.Maturity,zeros.Fwrd,color="orange",linewidth=0.5)
plt.ylim(0.,6.)
plt.title("Yield curve"+" ("+str(today.date())+")")
plt.xlabel("Maturity date")
plt.ylabel("Interest rate")
plt.gca().legend(('coupon term structure','bootstrapped zero rates',"P[F(t:T,T+3mo)], deg(P)=9","F(t,T,T+3mo)"),loc='upper left')
plt.show()














