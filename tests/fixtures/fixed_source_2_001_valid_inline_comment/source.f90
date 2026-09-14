      program p                                                         
      implicit none                                                     
      integer :: count                                                  
      count=0                                                           
      count=7! count=99; error stop 99!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
      count=count*2                                                     
      if (count/=14) error stop 1                                       
      end program p                                                     
