! rule: S11.1.3.2-002
! covers: associate-name-reads-expression-value
! Oracle values are derived from Fortran 2023 11.1.3.2 or 11.1.3.3.
program associate_construct_expression_associate_read_effect
  implicit none
  integer :: checks
  integer :: left, right
  left=12
  right=5
  checks=0
  ! expr_value identifies the evaluated expression entity throughout this block.
  associate (expr_value => left*10 + right)
    left=-1
    right=-2
  if (expr_value /= 125) then
    write(*,'(a)') 'ACF:expression_associate_read:expression-read'
    error stop
  end if
  checks=checks+1
  if (left /= -1) then
    write(*,'(a)') 'ACF:expression_associate_read:left-mutated-control'
    error stop
  end if
  checks=checks+1
  if (right /= -2) then
    write(*,'(a)') 'ACF:expression_associate_read:right-mutated-control'
    error stop
  end if
  checks=checks+1
  end associate
  if (checks /= 3) then
    write(*,'(a)') 'ACF:expression_associate_read:check-total'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE EXPRESSION ASSOCIATE READ OK'
end program associate_construct_expression_associate_read_effect
