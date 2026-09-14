      program inclusion                                                 
      implicit none                                                     
      integer :: value                                                  
      value = -9                                                        
      I N C L U D E'payload.inc'                                        
      if (value /= 23) stop 1                                           
      end program inclusion                                             
