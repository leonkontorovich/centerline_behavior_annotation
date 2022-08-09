import sys

#sys.path.append(str('/Volumes/scratch/neurobiology/zimmer/ulises/code/curvature_analysis/curvature_analysis-pkg'))
print(sys.path)

import pandas as pd
from curvature_analysis.dev.annotate_behaviour import *
from curvature_analysis.src.make_PCA import *

if __name__ == "__main__":

    import argparse
    import os
    import pandas as pd
    import numpy as np
    from curvature_analysis.dev.annotate_behaviour import *
    from curvature_analysis.src.make_PCA import *

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--i_path', help='input path', required=True)
    args = vars(parser.parse_args())
    main_path = args['i_path']


    pca_path='/scratch/neurobiology/zimmer/ulises/code/curvature_analysis/curvature_analysis-pkg/models/eignenworm_PCA_bodypart_30_to_80.pkl'
    df=pd.read_csv(os.path.join(main_path, 'skeleton_spline_K.csv', header=None))
    df.fillna(0, inplace=True)  # alternative change nans to zeros
    features = np.arange(30, 80)  # Separating out the features (starting bodypart, ending bodypart)
    data = df.loc[:, features].values
    principal_components_df = pca_transform_data(pca_path, data)
    #save PCs?
    #principal_components_df.to_csv(which_path)
    pc1_pc2_df = extract_vectors_from_PC_df(principal_components_df, avg_win=167)
    cross_product_df = calculate_cross_product(pc1_pc2_df)

    values_arr = binarize_cross_product(cross_product_df)
    values_df = pd.DataFrame(values_arr)
    values_df.to_csv(os.path.join(main_path, 'beh_annotation.csv'))