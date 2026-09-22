! rule: S10.1.5.5.1-010
! covers: right-blank-padding-equality
! covers: all-characters-equal
! Oracle truth values are hand-derived from Fortran 2023 10.1.5.5.1.
program rel_intrinsic_right_blank_padding_equality
  implicit none
  integer :: checks
  logical :: equal_result, unequal_result
  character(len=1) :: short
  character(len=2) :: padded
  checks=0
  short = 'A'
  padded = 'A '
  ! Padding extends short to 'A '; both corresponding default characters are equal.
  select case (len(short))
  case (1)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:right_blank_padding_equality:short-length'
    error stop
  end select
  select case (len(padded))
  case (2)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:right_blank_padding_equality:padded-length'
    error stop
  end select
  equal_result = short == padded
  if (.not. (equal_result)) then
    write(*,'(a)') 'RIF:right_blank_padding_equality:padding-equality-true'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (3)
  case default
    write(*,'(a)') 'RIF:right_blank_padding_equality:check-total'
    error stop
  end select
  write(*,'(a)') 'RELATIONAL INTRINSIC RIGHT BLANK PADDING EQUALITY OK'
end program rel_intrinsic_right_blank_padding_equality
