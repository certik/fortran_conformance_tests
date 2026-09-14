      program p                                                         
      implicit none                                                     
      integer :: x                                                      
      x=0                                                               
      call inner(x)                                                     
      if (x/=7) error stop 1                                            
      contains                                                          
      subroutine inner(value)                                           
      integer, intent(out) :: value                                     
      value=7                                                           
      en                                                                
     1d subroutine inner                                                
      end program p                                                     
