! rule: C1105
! covers: data-expression-selector-control
program ab_c1105_data
  implicit none
  integer :: base, result
  base=30; result=-1
  associate (data_expr => base + 12)
    result=data_expr
  end associate
  if (result /= 42) then
    write(*,'(a)') 'C1105'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS C1105 DATA OK'

end program ab_c1105_data
