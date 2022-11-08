# Discount-Factor-Term-Structure-using-python

Read in the treasuries data table and formated it.

url=http://www.wsj.com/mdc/public/page/2_3020-treasury.html

Calculated the time-to-maturity in years

Bootstraped the zero-curve for bonds observations. Semi-annual coupon payments is used with the coupon payments on

Set the ask price for the coupon bond, which all the coupons will be stripped from to attain the final zero price as the result.

Striped the coupons from the quoted bond Asks

Calculated the yield implied by the coupon bond's bootstrapped zero-coupon price

Constructed a 12-month rolling centered moving average of yields

Plotted the bills zero-curve

