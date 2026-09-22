! rule: S10.1.5.1-004
! covers: character-result-length-value
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_character_result_length_value
  implicit none
  integer :: checks
  character(len=2) :: left
  character(len=3) :: right
  character(len=5) :: result
  checks=0
  left = 'Lm'
  right = 'h5K'
  ! Assigning 'Lm' // 'h5K' observes length 2+3=5 and value 'Lmh5K'.
  result = left // right
  if (len(result) /= 5) then
    write(*,'(a)') 'IOC:character_result_length_value:result-length'
    error stop
  end if
  checks=checks+1
  if (result /= 'Lmh5K') then
    write(*,'(a)') 'IOC:character_result_length_value:result-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'IOC:character_result_length_value:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION CHARACTER RESULT LENGTH VALUE OK'
end program ioc_character_result_length_value
