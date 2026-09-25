program block_common_save_name
implicit none
integer :: outer_value
common /outer_block/ outer_value
block
  save /outer_block/
  outer_value=1
end block
end program block_common_save_name
