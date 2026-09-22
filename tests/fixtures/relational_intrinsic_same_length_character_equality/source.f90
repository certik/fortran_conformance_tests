! rule: S10.1.5.5.1-010
! covers: same-length-character-equality
! Oracle truth values are hand-derived from Fortran 2023 10.1.5.5.1.
program rel_intrinsic_same_length_character_equality
  implicit none
  integer :: checks
  logical :: equal_result, unequal_result
  character(len=2) :: left, same, different
  checks=0
  left = 'M5'
  same = 'M5'
  different = 'M6'
  ! Same length: 'M5' equals 'M5', while position 2 differs in 'M6'.
  select case (len(left))
  case (2)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:same_length_character_equality:left-length'
    error stop
  end select
  select case (len(same))
  case (2)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:same_length_character_equality:same-length'
    error stop
  end select
  select case (len(different))
  case (2)
    checks=checks+1
  case default
    write(*,'(a)') 'RIF:same_length_character_equality:different-length'
    error stop
  end select
  equal_result = left == same
  if (.not. (equal_result)) then
    write(*,'(a)') 'RIF:same_length_character_equality:same-length-equality-true'
    error stop
  end if
  checks=checks+1
  unequal_result = left == different
  if (unequal_result) then
    write(*,'(a)') 'RIF:same_length_character_equality:same-length-difference-false'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (5)
  case default
    write(*,'(a)') 'RIF:same_length_character_equality:check-total'
    error stop
  end select
  write(*,'(a)') 'RELATIONAL INTRINSIC SAME LENGTH CHARACTER EQUALITY OK'
end program rel_intrinsic_same_length_character_equality
