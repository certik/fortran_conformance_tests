      program p                                                         
      implicit none                                                     
      integer :: x                                                      
      x=0                                                               
      x=2                                                               
      x=x+5! x=99                                                       
      if (x/=7) error stop 1                                            
      end program p                                                     
