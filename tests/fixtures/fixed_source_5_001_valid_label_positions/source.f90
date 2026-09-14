      program p                                                         
      implicit none                                                     
      integer :: count                                                  
      count=0                                                           
      go to 1                                                           
      error stop 1                                                      
1     count=count+1                                                     
      go to 2                                                           
      error stop 1                                                      
 2    count=count+1                                                     
      go to 3                                                           
      error stop 1                                                      
  3   count=count+1                                                     
      go to 4                                                           
      error stop 1                                                      
   4  count=count+1                                                     
      go to 5                                                           
      error stop 1                                                      
    5 count=count+1                                                     
      go to 100                                                         
      error stop 2                                                      
1 0 0 count=count+1                                                     
      if (count/=6) error stop 3                                        
      end program p                                                     
