from arcpy import *
import numpy as np

#recuperation des parametres 
couche=GetParameterAsText(0)
chemin_couche_enveloppe_convexe=GetParameterAsText(1)

class PoinT:
    def __init__(self,x,y):
        self.x=x
        self.y=y

    # afin de trier les points en fonction de leur coordonnée x 
    def __lt__(self, other):
      return self.x < other.x

    def __str__(self):
      return '(%.1f,%.1f)' %(self.x,self.y)

#creation de la liste all points contenant toutes les points
aa=Describe(couche).shapeType
allPoints=[]
if aa=="Point":
    with da.SearchCursor(couche,["SHAPE@X","SHAPE@Y"]) as cursor:  #P la liste des objets Points
        for row in cursor:
            allPoints.append(PoinT(row[0],row[1]))
if aa=="Polyline":
    arcpy.GeneratePointsAlongLines_management(couche, "point_polyline", 'PERCENTAGE', Percentage=5)
    with da.SearchCursor("point_polyline",["SHAPE@X","SHAPE@Y"]) as curs:  #P la liste des objets Points
        for rows in curs:
            allPoints.append(PoinT(rows[0],rows[1]))    

if aa=="Polygon":
    arcpy.PolygonToLine_management(couche, "polygone_line","IGNORE_NEIGHBORS")
    arcpy.GeneratePointsAlongLines_management("polygone_line", "point_polyline", 'PERCENTAGE', Percentage=5)            
    with da.SearchCursor("point_polyline",["SHAPE@X","SHAPE@Y"]) as cur:  #P la liste des objets Points
        for rowss in cur:
            allPoints.append(PoinT(rowss[0],rowss[1]))

        

# Fonction qui renvoie vrai si le point p est a gauche de la ligne ab
def isLeftOf(p,a,b):
  return (np.sign((b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x)) >= 0 )

# Fonction qui renvoie vrai si le point p est a droite de la ligne ab
def isRightOf(p,a,b):
  return (np.sign((b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x)) <= 0 )

# Fonction qui renvoie vrai si le point p est la tangente superieure du point p
# q1 est le point precedent de p et q2 est le point suivant, lors d'un deplacement anti-horaire dans un polygone
def isUpperTangent(p, q, q1, q2):
  return isLeftOf(p,q,q2) and isRightOf(p,q1,q)

# Fonction qui renvoie vrai si le point p est la tangente inferieur du point p
def isLowerTangent(p, q, q1, q2):
  return isRightOf(p,q,q2) and isLeftOf(p,q1,q)

# Tri des points par leur coordonnée x
allPoints = sorted(allPoints)

# commencement par une coque(hull) triviale (un triangle des premiers points)
hullPoints = allPoints[:3]

# Stock des bords dans l'ordre antihoraire
hullEdge = {}
if (isRightOf(hullPoints[0], hullPoints[1], hullPoints[2])):
  hullEdge= {
      hullPoints[0]: {'prev': hullPoints[1], 'next': hullPoints[2]},
      hullPoints[1]: {'prev': hullPoints[2], 'next': hullPoints[0]},
      hullPoints[2]: {'prev': hullPoints[0], 'next': hullPoints[1]}
  }
else:
  hullEdge= {
      hullPoints[0]: {'prev': hullPoints[2], 'next': hullPoints[1]},
      hullPoints[2]: {'prev': hullPoints[1], 'next': hullPoints[0]},
      hullPoints[1]: {'prev': hullPoints[0], 'next': hullPoints[2]}
  }

n = len(allPoints)

# Un par un, ajout des sommets restants à la coque convexe
# et suppression des sommets qui se trouvent à l'intérieur
for i in range(3,n):
  pi = allPoints[i]
  

  # Soit j l'indice le plus à droite de la coque convexe
  j = len(hullPoints) - 1

  # Recherche du point tangent supérieur
  u = j
  upperTangent = hullPoints[u]
  while(not isUpperTangent(pi, upperTangent, hullEdge[upperTangent]['prev'], hullEdge[upperTangent]['next'])) and u >= 0:
    #print('- its not %s'%(upperTangent)) 
    u -= 1
    upperTangent = hullPoints[u]
  

  # Recherche de point tangent inférieur en itérantion sur les sommets 
  # précédent de upperTangent, un par un jusqu'à ce qu'il soit trouvé
  lowerTangent = hullEdge[upperTangent]['prev']
  while(not isLowerTangent(pi, lowerTangent, hullEdge[lowerTangent]['prev'], hullEdge[lowerTangent]['next'])):
      temp = lowerTangent
      lowerTangent = hullEdge[lowerTangent]['prev']
      hullEdge.pop(temp,None)
      hullPoints.remove(temp)

  # Mettre à jour la coque convexe en ajoutant le nouveau point
  hullPoints.append(pi)

  # Mettre à jour les bords
  hullEdge[pi] = {'prev': lowerTangent, 'next': upperTangent}
  hullEdge[lowerTangent]['next'] = pi
  hullEdge[upperTangent]['prev'] = pi
  

# Convertion des points et des arêtes en np.arrays afin de les afficher
pointsArray = list()
for point in allPoints:
  pointsArray.append([point.x, point.y])
pointsArray = np.array(pointsArray)

hullEdge[pi] = {'prev': lowerTangent, 'next': upperTangent}
hullArray = list()
point = hullPoints[0]
for i in range(len(hullPoints)):
  hullArray.append([point.x, point.y])
  point = hullEdge[point]['next']
hullArray.append(hullArray[0])
hullArray = np.array(hullArray)

#creation de A la liste de points de la coque convexe
A=Array()
for pt in hullArray:
    A.append(Point(pt[0],pt[1]))

# creation de la coque convexe
CreateFeatureclass_management(chemin_couche_enveloppe_convexe,"ConvexPolygonIncremental","POLYGON")

# insertion du polygon de la coque convexe
chemin=chemin_couche_enveloppe_convexe+"\\"+"ConvexPolygonIncremental.shp"
with da.InsertCursor(chemin,["Shape@"]) as cursor:
    cursor.insertRow([Polygon(A)])
