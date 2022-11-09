import os
def buildAssetDic(path):
    dic={}

    dic_variantSet={}


    variantSets = os.listdir(path)


    for variantSet in variantSets:

        variantSetDir = os.path.join(path,variantSet)
        variants = os.listdir(variantSetDir)
        dic_variant={}
        for variant in variants:

            variantDir = os.path.join(variantSetDir,variant)
            versions = os.listdir(variantDir)
            dic_variant[variant]=versions
        dic_variantSet[variantSet]=dic_variant


    return dic_variantSet
