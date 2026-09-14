      program p                                                         
      implicit none                                                     
      integer :: x, y                                                   
      x=0; y=0                                                          
      x=2;;;x=x+5; ; ;y=x+3;; ;                                         
      if (x/=7) error stop 1                                            
      if (y/=10) error stop 2                                           
      end program p                                                     
