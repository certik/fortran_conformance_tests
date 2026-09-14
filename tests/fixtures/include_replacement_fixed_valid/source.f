      program inclusion                                                 
      implicit none                                                     
      integer :: value                                                  
      value = 0                                                         
      include 'payload.inc'                                             
      if (value /= 21) stop 1                                           
      end program inclusion                                             
