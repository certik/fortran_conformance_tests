program data_statement_r841_matched_lists
  implicit none
  integer :: first, second
  data first, second /37, 41/
  if (first /= 37) error stop 1
  if (second /= 41) error stop 2
  write(*,'(a)') 'DATA STATEMENT R841 MATCHED LISTS OK'
end program data_statement_r841_matched_lists
