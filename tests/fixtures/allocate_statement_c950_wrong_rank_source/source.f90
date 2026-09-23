program allocate_statement_c950_wrong_rank_source
  implicit none
  integer, allocatable :: a(:)
  allocate(a(1:2), source=reshape([11,22,33,44],[2,2]))
end program allocate_statement_c950_wrong_rank_source
