      program p                                                         
      implicit none                                                     
      integer :: x, sentinel                                            
      x=0                                                               
      sentinel=0                                                        
      x=1                                                               
C    ! +99                                                              
*    ; +99                                                              
    !1+99                                                               
                                                                        
     1+2                                                                
C    & sentinel=99                                                      
      sentinel=7                                                        
      if (x/=3) error stop 1                                            
      if (sentinel/=7) error stop 2                                     
      end program p                                                     
