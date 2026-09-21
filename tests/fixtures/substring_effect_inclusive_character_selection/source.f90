program substring_inclusive_character_selection_effect
  implicit none
  character(len=3) :: c
  integer :: checks
  checks=0
  c='abc'
  if (c(2:2) /= 'b') then
    write(*,'(a)') 'SSE:inclusive_character_selection:single-endpoint-value'
    error stop
  end if
  checks=checks+1
  if (len(c(2:2)) /= 1) then
    write(*,'(a)') 'SSE:inclusive_character_selection:single-endpoint-length'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'SSE:inclusive_character_selection:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING INCLUSIVE CHARACTER SELECTION OK'
end program substring_inclusive_character_selection_effect
