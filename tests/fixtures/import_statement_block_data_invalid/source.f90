block data import_statement_c8100_block_data
  import
  integer :: value
  common /import_statement_c8100_common/ value
  data value /43/
end block data import_statement_c8100_block_data

program import_statement_c8100_block_data_control
  implicit none
  integer :: value
  common /import_statement_c8100_common/ value
  if (value /= 43) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 BLOCK DATA CONTROL OK'
end program import_statement_c8100_block_data_control
