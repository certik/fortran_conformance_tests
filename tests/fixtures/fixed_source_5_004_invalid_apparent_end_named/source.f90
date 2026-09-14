      program p                                                         
      implicit none                                                     
      integer :: endprogramp                                            
      endprogramp=0                                                     
      end program p                                                     
     1=7                                                                
      if (endprogramp/=7) error stop 1                                  
      end program p                                                     
