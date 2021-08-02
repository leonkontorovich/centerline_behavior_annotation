#import pckgs
import pandas as pd
from sklearn.decomposition import PCA
from pickle import dump
import numpy as np
import matplotlib.pyplot as plt

#i can do what ever i want since it is my branch

def make_eigenworm_PCA_model(K_df:pd.DataFrame,num_PCA_components:int=5,segments:list=None,output_folder:str=None):
    """
    Make a PCA model of all K data, for eigenworm analysis
    gets K values from skeleton csv file, and then computes the PCA model
    
    Parameters:
    -----------
    K_df: pd.DataFrame
        dataframe holding the K values
    num_PCA_components: int
       the number of PCA components to compute
    anotation_names:list
        names of anotation of head and then the tail.
    segments:list
        the number of the first bodypart segment to use for analysis
        default is 0, meaning the first one. 
        recommended to focus on middle body parts   
    """
    #remove NaNs
    no_nan_K_df = K_df.dropna()

    #focus on specific body segments PCA?
    if segments is None:
        first_body_part = 0
        last_body_part = K_df.shape[1]
    else:
        first_body_part = int(segments[0])
        last_body_part = int(segments[1])
        
    features = np.arange(first_body_part,last_body_part)# Separating out the features
    no_nan_K_df = no_nan_K_df.loc[:, features].values
        
    print("PCA is now performed on segments: "+str(first_body_part)+" to " +str(last_body_part))
    
    #get PCA
    pca = PCA(n_components=num_PCA_components)
    principal_components = pca.fit_transform(no_nan_K_df)    
    
    #if output folder save the pca weight model
    if output_folder is not None:
        dump(pca, open(output_folder+"eignenworm_PCA_bodypart_"+str(first_body_part)+"_to_"+str(last_body_part)+".pkl","wb"))
        print("saved pca in: "+output_folder+"pca.pkl")
    
    return pca

def concat_curvature_data(filelist:list, number_of_segments:int=100):
    """
    this function collects curvature data from a list of worm curvature files
    and returns a pandas dataframe with all the curvature together

    """
    K_df_all = pd.DataFrame(columns=np.arange(0,number_of_segments))

    for K_file in filelist:    
        K_df = pd.read_csv(K_file,names=np.arange(0,number_of_segments),index_col=False)
        if K_df.empty:
            continue
        else:
            K_df_all = K_df_all.append(K_df,ignore_index=True)

    print("\nFinished collecting curvature data!")
    print("In total: "+ str(K_df_all.shape[1]) + " segments in " +str(K_df_all.shape[0])+" frames")

    return K_df_all

def eigenworm_PCA_analysis(K_df,PCA_model,segments:list = None,output_path:str=None):
    """
    This function uses the PCA model to perform eigenworm analysis on worm curvature data
    The function gets the curvature dataframe and PCA model and computes the PC values
    per curvature values for every frame.
    
    Parameters:
    -----------
    K_df: pd.DataFrame
        dataframe holding the curvature values
    PCA_model: pca model
        PCA model to compute the PCs from the curvature data
    segments:list
        the number of start and end body segments out of all curvature dataframe
    """
    
    #remove NaNs but save NaN position for later
    nan_K = np.isnan(K_df)
    K_noNaN_pos = ~nan_K
    K_noNaN_pos = K_noNaN_pos.iloc[:,0]
    no_nan_K_df = K_df.dropna()
    
    #focus on specific body segments PCA?
    if segments is not None:
        first_body_part = int(segments[0])
        last_body_part = int(segments[1])
        #check number of segments fits PCA model
    else:
        first_body_part = 0
        last_body_part = K_df.shape[1]
        
    if int(PCA_model.n_features_) is not (last_body_part-first_body_part):
        print("the number of segments does not fit PCA model feature number")
        print("recieved: "+str(last_body_part-first_body_part)+" features but the model has "+str(PCA_model.n_features_)+" features!")

        
    #adjust the curvature dataframe to chosen segments
    features = np.arange(first_body_part,last_body_part)# Separating out the features
    no_nan_K_df = no_nan_K_df.loc[:,features].values
    
    #run pca model on K data
    principal_components = PCA_model.transform(no_nan_K_df)
    
    #initialize PCA DataFrame
    num_PCA_components = PCA_model.components_.shape[0]
    PCAs = list(range(1,num_PCA_components+1))
    PCA_columns = ["PCA" + str(i) for i in PCAs]
    principal_df = pd.DataFrame(data = principal_components, columns = PCA_columns)
    
    #return the NaN values
    eigenworm_PCA_df = pd.DataFrame(np.nan, index=np.arange(0,K_df.shape[0]), columns=principal_df.columns) 
    eigenworm_PCA_df.loc[K_noNaN_pos==True] = principal_df.values
    
    #save eigenworm dataframe as csv?
    if output_path is not None: eigenworm_PCA_df.to_csv(output_path+"_eigenworm_PCA_df.csv")
    
    return eigenworm_PCA_df

def plot_eigenworm_PCA_analysis(eigenworm_PCA_df:pd.DataFrame,num_PC_to_plot:int=2,start_frame:int=0,end_frame:int=None,ylim:list=None,xlim:list=None,output_path:str=None):
    """
    make plots of eignworm PCA analysis
    
    Parameters:
    -----------
    eigenworm_PCA_df: eigenworm PC dataframe
        dataframe holding the principal component values per frame
    PCA_model: pca model
        PCA model to compute the PCs from the curvature data
    num_PC_to_plot: int
        the number of PCs to plot
        default is 2.
    start_frame: int
        optional to restrict the plots to specific frames
        default is 0
    end_frame: int
        optional to restrict the plots to specific frames
        default is the end of the dataframe
    y and x lim: list
        optional to limit the axis of the plotted principal component values
        default None
    output_path: str
        optional to allow the user to save the plots
        default is None
    """
    
    #get PC names
    PCA_columns = eigenworm_PCA_df.columns
    
    #restrict figure to specific timeframe
    if end_frame is None:
        end_frame = eigenworm_PCA_df.shape[0] 
    frames=np.arange(start_frame,end_frame)
    
    ## plot change in first and second PCs
    fig = plt.figure(dpi=300)
    plt.rcParams.update({'font.size': 15})
    
    for pc in eigenworm_PCA_df:
        if pc is PCA_columns[num_PC_to_plot]: break #don't plot more then two PCs
        plt.ax=eigenworm_PCA_df.loc[frames,pc].plot(legend=True, figsize=(20,5), linewidth=2)
    plt.ax.set_xlabel('Time (frames)', fontsize = 15)
    plt.ax.set_ylabel('',fontsize = 15)
    if xlim is not None: plt.xlim(xlim)
    if ylim is not None: plt.ylim(ylim)
    plt.suptitle("Change in PC values across time, frames: "+str(start_frame)+" to "+str(end_frame))
    if output_path is not None: plt.savefig(output_path+"_PC_plot.png")
    plt.show()
    
    # plot principal component space
    plt.figure(dpi=300)
    plt.rcParams.update({'font.size': 10})
    avg_win_for_plot = 10
    x=eigenworm_PCA_df.loc[frames,PCA_columns[0]].rolling(window=avg_win_for_plot,center=True).mean()
    y=eigenworm_PCA_df.loc[frames,PCA_columns[1]].rolling(window=avg_win_for_plot,center=True).mean()
    sc = plt.scatter(x,y, c=np.arange(len(x)), s=1, cmap='viridis')
    cbar = plt.colorbar(sc)
    cbar.set_label('time (frames)')
    plt.scatter(x.to_numpy()[avg_win_for_plot+1],y.to_numpy()[avg_win_for_plot+1], c='g', edgecolors='k')
    plt.scatter(x.to_numpy()[-1],y.to_numpy()[-1], c='r', edgecolors='k')
    plt.xlabel(PCA_columns[0])
    plt.ylabel(PCA_columns[1])
    if xlim is not None: plt.xlim(xlim)
    if ylim is not None: plt.ylim(ylim)
    plt.suptitle("Principal component space")
    if output_path is not None: plt.savefig(output_path+"_PC_space_plot.png")
    plt.show()

def anotate_reversals_wCrossProduct(eigenworm_PCA_df:pd.DataFrame,rol_mean_window:int=5,output_path:str=None,plot_crossproduct:bool=False):
    """
    Anotate reversals using the cross product between PCs of two consecutive frames.
    the function recieves a dataframe holding the eigenworm principal components per frame
    the function then calcualtes the cross product between the first two principal components
    the function then anotates reversals based on the sign of the cross product
    
    Parameters:
    -----------
    eigenworm_PCA_df: eigenworm PC dataframe
        dataframe holding the principal component values per frame
    rol_mean_window:int
        rolling mean window size for smoothing of plot and calculations.
        default is 0.
    output_path: str
        optional -  path to the folder+name of recording to save figures
        default is None - i.e, no plotting.
    plot_crossproduct: bool
        should the crossproduct be plotted?
        default is False
    """
    #define first and second PCs
    #this assumes the first columns of the PCA dataframe are the first 2 PCs
    pc1 = eigenworm_PCA_df.iloc[:,0]
    pc2 = eigenworm_PCA_df.iloc[:,1]
    
    frames = np.arange(0,eigenworm_PCA_df.shape[0])
    
    #create crossproduct dataframe from series
    frame = { 'X': pc1, 'Y': pc2 } 
    cross_product_df=pd.DataFrame(data=frame)
    
    #calcualte cross product per frame
    ra=[np.nan] 
    for i, row in enumerate(cross_product_df.iterrows()):
        if i==len(cross_product_df)-1: continue
        r=np.cross([cross_product_df['X'].values[i],cross_product_df['Y'].values[i]],[cross_product_df['X'].values[i+1],cross_product_df['Y'].values[i+1]])
        ra.append(r)
    cross_product_df['Cross Product']=ra

    cross_product_df_rolMean = cross_product_df.loc[frames,'Cross Product'].rolling(window=rol_mean_window,center=True).mean()

    #save cross product results?
    if plot_crossproduct == True and output_path is not None: 
        cross_product_df.to_csv(output_path+"_crossProduct.csv")
        cross_product_df_rolMean.to_csv(output_path+"_crossProductRollMean.csv")

    #plot cross product
    if plot_crossproduct == True:
        plt.figure(dpi=300)
        plt.plot(cross_product_df.loc[frames,'Cross Product'], label='raw')
        plt.plot(cross_product_df_rolMean, alpha=.5, c='r', label='mov mean')
        plt.axhline(y=0, alpha=0.2, linestyle='--')
        plt.title('Cross Product')
        plt.ylabel('Cross Product')
        plt.xlabel('Time (frames)')
        plt.legend()

    #decide on threshold for reversals in cross product
    cross_products = cross_product_df_rolMean #cross_product_df['Cross Product']

    #should it be larger then 0 or bellow 0???

    reversals_df = cross_products<0 
    
    #convert NaNs to False
    reversals_df[np.isnan(cross_products)] = False
    #alterantive solution cross_product_df['Cross Product'].fillna(0,inplace=True)
    
    #save reversals to csv?
    if output_path is not None: reversals_df.to_csv(output_path+"_reversals.csv")
        
    return reversals_df

### WE SHOULD DECIDE IF WE CONTINUE WITH v1 or v2!!!

def annotate_reversals_wCrossProduct2(eigenworm_PCA_df:pd.DataFrame,rol_mean_window:int=5,interpolate_window:int=5,return_cross_product:bool=False,debug:bool=False):
    """
    Anotate reversals using the cross product between PCs of two consecutive frames.
    the function recieves a dataframe holding the eigenworm principal components per frame
    the function then calcualtes the cross product between the first two principal components
    the function then anotates reversals based on the sign of the cross product
    and returns both reversals and cross product
    
    Parameters:
    -----------
    eigenworm_PCA_df: eigenworm PC dataframe
        dataframe holding the principal component values per frame
    rol_mean_window:int
        rolling mean window size for smoothing of plot and calculations.
        default is 0.
    """
    #define first and second PCs
    #this assumes the first columns of the PCA dataframe are the first 2 PCs
    pc1 = eigenworm_PCA_df.iloc[:,0]
    pc2 = eigenworm_PCA_df.iloc[:,1]
    
    frames = np.arange(0,eigenworm_PCA_df.shape[0])
    
    #create crossproduct dataframe from series
    frame = { 'X': pc1, 'Y': pc2 } 
    cross_product_df=pd.DataFrame(data=frame)
    
    #calcualte cross product per frame
    ra=np.empty(1)
    ra[:] = np.NaN
    
    for i, row in enumerate(cross_product_df.iterrows()):
        if i==len(cross_product_df)-1: continue
        r=np.cross([cross_product_df['X'].values[i],cross_product_df['Y'].values[i]],[cross_product_df['X'].values[i+1],cross_product_df['Y'].values[i+1]])
        ra= np.append(ra,r)
    cross_product_df['cross_product']=ra
    
    #if no window to interpolate then, skip interpolation 
    if interpolate_window < 1:
        cross_product_df_interpolated =  cross_product_df.loc[frames,'cross_product']
    #if there's something to interpolate then interpolate then rolling mean
    else:
        cross_product_df_interpolated = cross_product_df.loc[frames,'cross_product'].interpolate(limit=interpolate_window)
    
    #perform rolling mean
    #if window too small, then skip rolling mean
    if rol_mean_window < 1:
        cross_product_df_int_roll = cross_product_df_interpolated
    else:
        cross_product_df_int_roll = cross_product_df_interpolated.rolling(rol_mean_window,center=True).mean()
    
    #decide on threshold for reversals in cross product
    if debug == True:print("input")
    if debug == True:print(eigenworm_PCA_df)
    if debug == True:print("original cross product")
    if debug == True:print(cross_product_df['cross_product'])
    
    cross_products = cross_product_df_int_roll 
    
    if debug == True:print("cross-product")
    if debug == True:print(cross_products)
    
    #should it be larger then 0 or bellow 0???
    reversals_df = cross_products<0 
    
    if debug == True:print("reversals")
    if debug == True:print(reversals_df)
    
    #make sure we keep the nan values
    nan_values_series = pd.isnull(cross_products)
    
    if debug == True:print("nans")
    if debug == True:print(nan_values_series)
    if debug == True:print("value counts of nan\n",nan_values_series.value_counts())
    
    reversals_df[nan_values_series==True] = np.nan
    
    if debug == True:print("final reversals")
    if debug == True:print(reversals_df)
    
    if return_cross_product == True:
        return cross_products,reversals_df
    else:
        return reversals_df


####

import math
 
def get_angular_speed(hd5_df:pd.DataFrame,head_anotation:str='head'):
    """
    This function gets the head xy data from DLC anotations h5 file
    the function then calculates the angular speed per 2 consequtive frames
    the function returns a pandas dataframe with angular speed per frame

    Parameters
    -----------
    h5_df: pandas dataframe,
        pandas dataframe holding the h5 file with all the xy positions
    head_anotation: str
        string holding the name of the specific anotation you want to get angular speed from
    -----------
    Returns a DataFrame with angular speed per frame
    """
    #find general parameters
    total_time = hd5_df.shape[0]
    DLC_run_name = hd5_df.columns[0][0]
    
    
    #initialize the angular speed df
    idx = pd.Index(np.arange(0,total_time),name='frames')
    angular_speed_df = pd.DataFrame(index=idx,columns=['angular_speed'])
    
    prev_head_xy = None
    
    for timepoint in np.arange(0,total_time):
        head_x=hd5_df.loc[timepoint,:][DLC_run_name][head_anotation]['x'].astype(int)
        head_y=hd5_df.loc[timepoint,:][DLC_run_name][head_anotation]['y'].astype(int)
        head_xy = (head_x,head_y)

        if prev_head_xy is not None:
            angle = math.atan2(head_xy[0]-prev_head_xy[0],head_xy[1]-prev_head_xy[1])        
            angular_speed_df['angular_speed'].loc[timepoint] = angle
    
        prev_head_xy = head_xy
    
    angular_speed_df = angular_speed_df.rolling(window=5,center=True).mean()
    return angular_speed_df


import tifffile as tiff
import os 
from tqdm.notebook import tqdm

def make_reversal_anotated_movie(input_movie_path:str,reversal_df:pd.DataFrame,output_path:str=None):
    print(str(reversal_df["Cross Product"].shape[0]))
    
    #get output path from input path
    if output_path is None:
        recording_name = os.path.splitext(os.path.basename(input_movie_path))[0]
        folder_path = os.path.dirname(input_image) ## directory of file
        output_path = folder_path+recording_name

    with tiff.TiffWriter(output_path+"_wRevrsal_anotations.tiff", bigtiff=True) as tif_writer:
        with tiff.TiffFile(input_movie_path, multifile=False) as tif:
            for i, page in tdqm(enumerate(tif.pages)):
                img=page.asarray()
                
#                 #report every 500 frames
#                 if i % 500 == 0:
#                     print("now processing frame number: "+reversal_df.iloc[i])
#                 update_progress(i/len(tif.pages))
    
                #add a stripe on the frame to anotate a reversal
                
                if i < int(reversal_df["Cross Product"].shape[0]):
                    if reversal_df["Cross Product"].iloc[i] == True:
                        img[0:10,:] = 100
                else:
                    print("warning: length of anotation < length of movie")

                tif_writer.save(img)
                
    print("Finished!!!")

def heatmap2d(arr: np.ndarray,v_min=-0.6,v_max=0.6):
    figure = plt.figure(figsize=(10,5))
    plt.imshow(arr.T,origin="lower",cmap='seismic',vmin=v_min,vmax=v_max)
    plt.colorbar()
    return figure
