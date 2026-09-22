! rule: S10.1.5.5.1-010
! covers: zero-length-equality
! Oracle truth values are hand-derived from Fortran 2023 10.1.5.5.1.
program rel_intrinsic_zero_length_equality
  implicit none
  integer :: checks
  logical :: equal_result, unequal_result
  character(len=0) :: left, right
  checks=0
  left = ''
  right = ''
  ! Both operands have zero length; p8 says x1 is equal to x2 without indexing.
  select case (len(left))
  case (0)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:zero_length_equality:left-zero-length'
    error stop
  end select
  select case (len(right))
  case (0)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:zero_length_equality:right-zero-length'
    error stop
  end select
  equal_result = left == right
  if (.not. (equal_result)) then
    write(*,'(a)') 'RIF:zero_length_equality:zero-length-equality-true'
    error stop
  end if
  checks=checks+1
  unequal_result = left /= right
  if (unequal_result) then
    write(*,'(a)') 'RIF:zero_length_equality:zero-length-inequality-false'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (4)
  case default
    write(*,'(a)') 'RIF:zero_length_equality:check-total'
    error stop
  end select
  write(*,'(a)') 'RELATIONAL INTRINSIC ZERO LENGTH EQUALITY OK'
end program rel_intrinsic_zero_length_equality
