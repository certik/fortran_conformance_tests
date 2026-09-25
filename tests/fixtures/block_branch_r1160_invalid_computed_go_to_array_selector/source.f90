program computed_go_to_array_selector
implicit none
integer :: idx(1)
idx=[1]
go to (100), idx
100 continue
end program computed_go_to_array_selector
