! rule: C1102
! covers: distinct-associate-names-control
program ab_c1102_distinct
  implicit none
  integer :: x, y, result
  x=4; y=8; result=-1
  associate (left => x, right => y)
    result=left*10+right
  end associate
  if (result /= 48) then
    write(*,'(a)') 'C1102'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS C1102 DISTINCT OK'

end program ab_c1102_distinct
