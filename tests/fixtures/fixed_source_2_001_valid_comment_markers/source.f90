C    ! error stop 91; count=91                                          
c    ; error stop 92; count=92                                          
*    ! error stop 93; count=93                                          
! error stop 94; count=94                                               
 ! error stop 94; count=94                                              
  ! error stop 94; count=94                                             
   ! error stop 94; count=94                                            
    ! error stop 94; count=94                                           
      ! error stop 95; count=95                                         
                                                                       !
                                                                        
      program p                                                         
      implicit none                                                     
      integer :: count                                                  
      count=0                                                           
C    ! error stop 91; count=91                                          
c    ; error stop 92; count=92                                          
*    ! error stop 93; count=93                                          
! error stop 94; count=94                                               
 ! error stop 94; count=94                                              
  ! error stop 94; count=94                                             
   ! error stop 94; count=94                                            
    ! error stop 94; count=94                                           
      ! error stop 95; count=95                                         
                                                                       !
                                                                        
      count=7                                                           
      if (count/=7) error stop 1                                        
      end program p                                                     
C    ! error stop 91; count=91                                          
c    ; error stop 92; count=92                                          
*    ! error stop 93; count=93                                          
! error stop 94; count=94                                               
 ! error stop 94; count=94                                              
  ! error stop 94; count=94                                             
   ! error stop 94; count=94                                            
    ! error stop 94; count=94                                           
      ! error stop 95; count=95                                         
                                                                       !
                                                                        
