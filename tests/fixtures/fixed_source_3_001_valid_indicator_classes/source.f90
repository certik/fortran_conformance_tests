      program p                                                         
      implicit none                                                     
      integer :: x                                                      
      x=0                                                               
C    ; x=99                                                             
*    ! x=98                                                             
    !;x=97                                                              
     1+1                                                                
     9+1                                                                
     A+1                                                                
     a+1                                                                
     C+1                                                                
     c+1                                                                
     _+1                                                                
     &+1                                                                
     *+1                                                                
     !+1                                                                
     ;+1                                                                
      if (x/=11) error stop 1                                           
      end program p                                                     
