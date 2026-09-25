! rule: C1106
! covers: matching-associate-construct-name-control
program ab_c1106_matching
  implicit none
  integer :: x
  x=5
  outer: associate (a => x)
    a=55
  end associate outer
  if (x /= 55) then
    write(*,'(a)') 'C1106'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS C1106 MATCHING OK'

end program ab_c1106_matching
