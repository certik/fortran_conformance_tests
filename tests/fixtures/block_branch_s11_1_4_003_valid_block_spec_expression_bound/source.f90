program block_spec_expression_bound
implicit none
integer :: n, observed_size, observed_value
n=3
observed_size=-1
observed_value=-1
block
  integer :: local_values(n+1)
  local_values=[11,13,17,19]
  observed_size=size(local_values)
  observed_value=local_values(4)
end block
if (observed_size /= 4) error stop 1
if (observed_value /= 19) error stop 2
write(*,'(a)') 'BLOCK SPEC EXPRESSION OK'
end program block_spec_expression_bound
