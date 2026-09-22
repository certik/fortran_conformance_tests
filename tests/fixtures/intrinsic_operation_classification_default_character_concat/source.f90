! rule: S10.1.5.1-004
! covers: default-character-concat
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_default_character_concat
  implicit none
  integer :: checks
  character(len=2) :: left
  character(len=3) :: right
  checks=0
  left = 'Q3'
  right = 'z9X'
  ! 'Q3' // 'z9X' has default character kind, length 2+3=5, and value 'Q3z9X'.
  if (kind(left // right) /= kind(left)) then
    write(*,'(a)') 'IOC:default_character_concat:concat-kind'
    error stop
  end if
  checks=checks+1
  if (len(left // right) /= 5) then
    write(*,'(a)') 'IOC:default_character_concat:concat-length'
    error stop
  end if
  checks=checks+1
  if (left // right /= 'Q3z9X') then
    write(*,'(a)') 'IOC:default_character_concat:concat-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 3) then
    write(*,'(a)') 'IOC:default_character_concat:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION DEFAULT CHARACTER CONCAT OK'
end program ioc_default_character_concat
