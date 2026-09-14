      program p                                                         
      implicit none                                                     
      integer :: x, y                                                   
      x=0                                                               
      y=0                                                               
      x=1                                                               
     0x=2                                                               
      y=3                                                               
      y=4                                                               
      if (x/=2.or.y/=4) error stop 1                                    
      end program p                                                     
