program substring_contiguous_portion_effect
  implicit none
  character(len=6) :: c
  integer :: checks
  checks=0
  c='abcdef'
  if (c(2:5) /= 'bcde') then
    write(*,'(a)') 'SSE:contiguous_portion:contiguous-value'
    error stop
  end if
  checks=checks+1
  c(3:4)='XY'
  if (c(2:5) /= 'bXYe') then
    write(*,'(a)') 'SSE:contiguous_portion:contiguous-mutated-middle'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'SSE:contiguous_portion:check-total'
    error stop
  end if
  write(*,'(a)') 'SUBSTRING CONTIGUOUS PORTION OK'
end program substring_contiguous_portion_effect
