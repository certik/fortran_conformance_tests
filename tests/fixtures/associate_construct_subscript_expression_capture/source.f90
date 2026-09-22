! rule: S11.1.3.2-001
! covers: variable-designator-subexpressions-before-block
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_subscript_expression_capture_effect
  implicit none
  integer :: checks
  integer :: idx
  integer :: a(1:4)
  a=[11,22,33,44]
  idx=2
  checks=0
  ! idx in a(idx) is evaluated before the block; changing idx to 4 must not retarget cell.
  associate (cell => a(idx))
    idx=4
    cell=77
  end associate
  if (a(2) /= 77) then
    write(*,'(a)') 'ACF:subscript_expression_capture:captured-element-updated'
    error stop
  end if
  checks=checks+1
  if (a(4) /= 44) then
    write(*,'(a)') 'ACF:subscript_expression_capture:deferred-index-not-updated'
    error stop
  end if
  checks=checks+1
  if (idx /= 4) then
    write(*,'(a)') 'ACF:subscript_expression_capture:index-change-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'ACF:subscript_expression_capture:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE SUBSCRIPT EXPRESSION CAPTURE OK'
end program associate_construct_subscript_expression_capture_effect
