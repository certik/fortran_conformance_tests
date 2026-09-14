      program p                                                         
      implicit none                                                     
      integer :: x                                                      
      x=0                                                               
      10 continue                                                       
      x=3                                                               
      if (x/=3) error stop 1                                            
      end program p                                                     
