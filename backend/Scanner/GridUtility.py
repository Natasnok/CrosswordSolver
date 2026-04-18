class Grid:
    '''
    E -> nbligne:int ; nbcolonne:int ; pos_bloc_noir: list[(int,int)]( default=[] )
    '''
    def __init__(self,nbligne:int,nbcolonne:int,pos_bloc_noir:list[(int,int)]=[]):
        self.nbline=nbligne
        self.nbcolonne=nbcolonne
        self.grid=[[0 for _ in range(nbcolonne)]for _ in range(nbligne)]
        self.blocNoir=pos_bloc_noir
        if pos_bloc_noir:
            for pos in pos_bloc_noir:
                self.poserBlocNoir(pos)
        
    def poserBlocNoir(self,pos:tuple[int,int]):
        x,y = pos
        self.grid[x][y] = 1
        if pos not in self.blocNoir:
            self.blocNoir.add(pos)
    
    def get_info_word(self):
        '''
        Renvoie la data Horizontale puis Verticale
        Sortie -> [(1,{"pos";"len;"dir}),(2,{"pos";"len;"dir}),...etc]
        '''

        mots_horizontale = self.__get_infoMotHorizontale() 
        mots_verticale = self.__get_infoMotVerticale() 
        return list(enumerate(mots_horizontale + mots_verticale)) #[(1,{"pos";"len;"dir}),(2,{"pos";"len;"dir}),...etc]

    def __get_infoMotHorizontale(self):
        mots=[]
        for i in range(self.nbline):
            j = 0
            while j < self.nbcolonne:

                if self.grid[i][j] == 0 and (j == 0 or self.grid[i][j-1] == 1):
                    start_j = j
                    length = 0

                    while j < self.nbcolonne and self.grid[i][j] == 0:
                        length += 1
                        j += 1

                    if length > 1:
                        mots.append({"pos": (start_j, i),"len": length,"dir": "H"})
                else:
                    j += 1
        return mots
    
    def __get_infoMotVerticale(self):
        mots=[]
        for j in range(self.nbcolonne):
            i = 0
            while i < self.nbline:
                if self.grid[i][j] == 0 and (i == 0 or self.grid[i-1][j] == 1):
                    start_i = i
                    length = 0

                    while i < self.nbline and self.grid[i][j] == 0:
                        length += 1
                        i += 1

                    if length > 1:
                        mots.append({"pos": (j, start_i),"len": length,"dir": "V"})
                else:
                    i += 1

        return mots
