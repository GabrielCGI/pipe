strength = mel.eval('pgYetiGroomCtxCommand -q -brushStrength pgYetiGroomCtxCommand1;')
invertStrength = -1 * strength
mel.eval('pgYetiGroomCtxCommand -e -brushStrength '+str(invertStrength)+' pgYetiGroomCtxCommand1;')