'''
Adapted from https://github.com/ddm7018/Elo
'''

class Elo:

    def __init__(self,k,g=1):
        self.ratingDict = {}	
        self.k = k
        self.g = g

    def addPlayer(self,name,rating = 1500):
        self.ratingDict[name] = rating
		
    def gameOver(self, winner, loser):
        result = self.expectResult(self.ratingDict[winner], self.ratingDict[loser])
        self.ratingDict[winner] = self.ratingDict[winner] + int((self.k*self.g) * (1 - result))  
        self.ratingDict[loser] 	= self.ratingDict[loser] + int((self.k * self.g) * (result - 1))
		
    def expectResult(self, p1, p2):
        exp = (p2 - p1) / 400.0
        return 1 / ((10.0 ** (exp)) + 1)
