program data_statement_s004_vector_section_order
  implicit none
  integer :: a(4)
  data a([4,1,3]) /41, 11, 31/
  if (a(4) /= 41) error stop 1
  if (a(1) /= 11) error stop 2
  if (a(3) /= 31) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 VECTOR SECTION ORDER OK'
end program data_statement_s004_vector_section_order
