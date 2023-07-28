from scipy.optimize import minimize_scalar
from scipy.optimize import root_scalar
from scipy import optimize

def twoOutcomeKellyStake(odds, prob):
    return (prob * odds - (1 - prob))/odds

def threeOutcomeKellyStake(oddsA, probA, oddsB, probB):
    func = lambda x : (-(1 - probA - probB)/(1-x)) + (probA * oddsA / (1 + oddsA * x)) + (probB * oddsB / (1 + oddsB * x))
    #res = minimize_scalar(func, method='brent')
    res = optimize.root_scalar(func, bracket=[0, 0.99], method='brentq')
    return(res.root)

# x = threeOutcomeKellyStake(10,0.2, 30, 0.1)
# print(x)

# x = twoOutcomeKellyStake(10,0.2)
# print(x)
