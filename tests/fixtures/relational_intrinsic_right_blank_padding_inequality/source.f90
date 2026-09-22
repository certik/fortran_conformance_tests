! rule: S10.1.5.5.1-010
! covers: right-blank-padding-inequality
! Oracle truth values are hand-derived from Fortran 2023 10.1.5.5.1.
program rel_intrinsic_right_blank_padding_inequality
  implicit none
  integer :: checks
  logical :: equal_result, unequal_result
  character(len=1) :: short
  character(len=4) :: long
  checks=0
  short = 'A'
  long = 'A  B'
  ! Padding extends short to 'A   '; first difference is position 4, blank versus 'B'.
  select case (len(short))
  case (1)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:right_blank_padding_inequality:short-length'
    error stop
  end select
  select case (len(long))
  case (4)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:right_blank_padding_inequality:long-length'
    error stop
  end select
  equal_result = short == long
  if (equal_result) then
    write(*,'(a)') 'RIF:right_blank_padding_inequality:padding-inequality-equality-false'
    error stop
  end if
  checks=checks+1
  unequal_result = short /= long
  if (.not. (unequal_result)) then
    write(*,'(a)') 'RIF:right_blank_padding_inequality:padding-inequality-not-equal-true'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (4)
  case default
    write(*,'(a)') 'RIF:right_blank_padding_inequality:check-total'
    error stop
  end select
  write(*,'(a)') 'RELATIONAL INTRINSIC RIGHT BLANK PADDING INEQUALITY OK'
end program rel_intrinsic_right_blank_padding_inequality
