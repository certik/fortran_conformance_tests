program data_statement_s004_component_section_order
  implicit none
  type :: cell
    integer :: value
  end type cell
  type(cell) :: cells(3)
  data cells(:)%value /13, 29, 47/
  if (cells(1)%value /= 13) error stop 1
  if (cells(2)%value /= 29) error stop 2
  if (cells(3)%value /= 47) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 COMPONENT SECTION ORDER OK'
end program data_statement_s004_component_section_order
