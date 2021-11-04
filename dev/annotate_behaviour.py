#The functions here should help generating behaviour annotations based on PCA (and other parameters)

#extract vectors from PC space
def extract_vectors_from_PC_df(df):
    """"
    extracts PC1 and PC2 from PC dataframe (principalDf)

    """
    x = df.loc[time, 'PC1']
    y = df.loc[time, 'PC2']
    return x,y

#calculate cross product
def calculate_cross_product(principalDf,avg_wing):
    """"
    """
    x = principalDf.loc[time, 'PC1'].rolling(window=avg_win).mean()
    y = principalDf.loc[time, 'PC2'].rolling(window=avg_win).mean()

    frame = {'X': x, 'Y': y}
    cross_product_df = pd.DataFrame(data=frame)

    ra = [np.array(np.nan)]  # before was np.nan
    for i, row in enumerate(cross_product_df.iterrows()):
        if i == len(cross_product_df) - 1: continue

        vector_a=[cross_product_df['X'].values[i], cross_product_df['Y'].values[i]]
        vector_b=[cross_product_df['X'].values[i + 1], cross_product_df['Y'].values[i + 1]
        r = np.cross(a,b)
    return cross_product
#smoothen cross product

#binarize cross product

#generate pandas dataframe or vector or wahtever with Forward and Reversal annotation

#Further behavioural annotation:
    #Turns and Dorsal Turns, Ventral Turns