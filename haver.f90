 
      function to_radian(degree) result(rad)
          ! degrees to radians
          real,intent(in) :: degree
          real, parameter :: deg_to_rad = atan(1.0)/45 ! exploit intrinsic atan to generate pi/180 runtime constant
          real :: rad
 
          rad = degree*deg_to_rad
      end function to_radian
 
      function haversine(deglat1,deglon1,deglat2,deglon2) result (dist)
          ! great circle distance -- adapted from Matlab 
          real,intent(in) :: deglat1,deglon1,deglat2,deglon2
          real :: a,c,dist,dlat,dlon,lat1,lat2
          real,parameter :: radius = 3956
 
          dlat = to_radian(deglat2-deglat1)
          dlon = to_radian(deglon2-deglon1)
          lat1 = to_radian(deglat1)
          lat2 = to_radian(deglat2)
          a = (sin(dlat/2))**2 + cos(lat1)*cos(lat2)*(sin(dlon/2))**2
          c = 2*asin(sqrt(a))
          dist = radius*c
      end function haversine

      function haverdist(lat,lon,n) result(distvech)
        integer :: n
        real,dimension(n) ::  lat,lon
        real,dimension(n*(n-1)/2) :: distvech
        integer :: i,j,k
        k=1
        distvech=0.0
        do i=1,n
           do j=1,(i-1)
             distvech(k)= haversine(lat(i),lon(i),lat(j),lon(j))
             k=k+1
           enddo
        enddo
      end function haverdist

       function havermatrix(lat,lon,n) result(distM)
        integer :: n
        real,dimension(n) :: lat,lon
        real,dimension(n,n) :: distM
        integer :: i,j
        distM=0.0
        do i=1,n
           do j=1,(i-1)
             distM(i,j)= haversine(lat(i),lon(i),lat(j),lon(j))
             distM(j,i)=distM(i,j)
           enddo
        enddo
      end function havermatrix
 
