      program inclusion                                                 
      implicit none                                                     
      integer :: value                                                  
      value = -9                                                        
      include 'payload.inc'                                             
      value = value + 1                                                 
      if (value /= 24) stop 1                                           
      end program inclusion                                             
