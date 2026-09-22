! rule: S10.1.5.3.1-001
! covers: character-result-type
! Character value comparisons use equal-length expected literals; each length claim uses LEN.
program exact_arithmetic_character_result_type
  implicit none
  integer :: checks
  character(len=2) :: left
  character(len=3) :: right
  character(len=5) :: result
  checks=0
  left = 'R4'
  right = 's9T'
  ! Assigning 'R4' // 's9T' to CHARACTER(LEN=5) observes a character result value 'R4s9T'.
  result = left // right
  if (result /= 'R4s9T') then
    write(*,'(a)') 'EAF:character_result_type:assigned-character-value'
    error stop
  end if
  checks=checks+1
  if (len(result) /= 5) then
    write(*,'(a)') 'EAF:character_result_type:assigned-character-length'
    error stop
  end if
  checks=checks+1
  if (kind(result) /= kind(left)) then
    write(*,'(a)') 'EAF:character_result_type:assigned-character-kind'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'EAF:character_result_type:check-total'
    error stop
  end if
  write(*,'(a)') 'EXACT ARITHMETIC CHARACTER RESULT TYPE OK'
end program exact_arithmetic_character_result_type
