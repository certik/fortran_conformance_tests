program data_statement_s004_triplet_section_order
  implicit none
  integer :: a(6)
  data a(2:6:2) /21, 43, 65/
  if (a(2) /= 21) error stop 1
  if (a(4) /= 43) error stop 2
  if (a(6) /= 65) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 TRIPLET SECTION ORDER OK'
end program data_statement_s004_triplet_section_order
