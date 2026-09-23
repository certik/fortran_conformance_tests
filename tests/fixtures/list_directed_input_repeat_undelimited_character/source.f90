! rule: S13.10.3.1-002
! covers: repeat-undelimited-character
! Oracle values are hand-derived from Fortran 2023 13.10.2, 13.10.3.1, or 13.10.3.2.
program list_directed_input_repeat_undelimited_character
  implicit none
  integer :: checks, stray
  character(len=4) :: rec
  character(len=2) :: words(2)
  checks=0
  stray=-909
  words=[character(len=2) :: 'QQ','RR']
  rec = "2*ab"
  read(rec,*) words
  if (len(words(1)) /= 2) then
    write(*,'(a)') 'LDI:repeat_undelimited_character:word1-len'
    error stop
  end if
  checks=checks+1
  if (words(1) /= 'ab') then
    write(*,'(a)') 'LDI:repeat_undelimited_character:word1'
    error stop
  end if
  checks=checks+1
  if (len(words(2)) /= 2) then
    write(*,'(a)') 'LDI:repeat_undelimited_character:word2-len'
    error stop
  end if
  checks=checks+1
  if (words(2) /= 'ab') then
    write(*,'(a)') 'LDI:repeat_undelimited_character:word2'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'LDI:repeat_undelimited_character:check-total'
    error stop
  end if
  write(*,'(a)') 'LIST DIRECTED INPUT REPEAT UNDELIMITED CHARACTER OK'
end program list_directed_input_repeat_undelimited_character
