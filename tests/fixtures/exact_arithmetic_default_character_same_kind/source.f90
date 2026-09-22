! rule: S10.1.5.3.1-001
! covers: default-character-same-kind
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_default_character_same_kind
  implicit none
  integer :: checks
  character(len=2) :: left
  character(len=3) :: right
  checks=0
  left = 'AX'
  right = 'b7q'
  ! 'AX' // 'b7q' appends the right operand, giving length 2+3=5 and value 'AXb7q'.
  if (kind(left) /= kind(right)) then
    write(*,'(a)') 'EAF:default_character_same_kind:default-operands-same-kind'
    error stop
  end if
  checks=checks+1
  if (kind(left // right) /= kind(left)) then
    write(*,'(a)') 'EAF:default_character_same_kind:default-result-kind'
    error stop
  end if
  checks=checks+1
  if (len(left // right) /= 5) then
    write(*,'(a)') 'EAF:default_character_same_kind:default-result-length'
    error stop
  end if
  checks=checks+1
  if (left // right /= 'AXb7q') then
    write(*,'(a)') 'EAF:default_character_same_kind:default-result-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'EAF:default_character_same_kind:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC DEFAULT CHARACTER SAME KIND OK'
end program exact_arithmetic_default_character_same_kind
