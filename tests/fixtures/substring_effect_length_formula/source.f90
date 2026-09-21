program substring_length_formula_effect
  implicit none
  character(len=6) :: c
  integer :: checks
  checks=0
  c='abcdef'
  if (len(c(2:4)) /= 3) then
    write(*,'(a)') 'SSE:length_formula:length-three'
    error stop
  end if
  checks=checks+1
  if (c(2:4) /= 'bcd') then
    write(*,'(a)') 'SSE:length_formula:length-three-value'
    error stop
  end if
  checks=checks+1
  if (len(c(4:4)) /= 1) then
    write(*,'(a)') 'SSE:length_formula:length-one'
    error stop
  end if
  checks=checks+1
  if (c(4:4) /= 'd') then
    write(*,'(a)') 'SSE:length_formula:length-one-value'
    error stop
  end if
  checks=checks+1
  if (len(c(4:3)) /= 0) then
    write(*,'(a)') 'SSE:length_formula:length-zero'
    error stop
  end if
  checks=checks+1
  if (c(4:3) /= '') then
    write(*,'(a)') 'SSE:length_formula:length-zero-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'SSE:length_formula:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING LENGTH FORMULA OK'
end program substring_length_formula_effect
