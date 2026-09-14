! rule: R610
! covers: concat-op
! evidence: positive-control
module r610_concat_m
    implicit none
    type :: chunk
        character(len=2) :: text
    end type chunk
    interface operator (//)
        module procedure join_chunks
    end interface
contains
    function join_chunks(left, right) result(value)
        type(chunk), intent(in) :: left, right
        character(len=4) :: value
        value = left%text // right%text
    end function join_chunks
end module r610_concat_m

program extended_concat
    use r610_concat_m
    implicit none
    type(chunk) :: left, right
    character(len=4) :: result

    left%text = 'ab'
    right%text = 'CD'
    result = left // right
    if (result /= 'abCD') error stop 1
end program extended_concat
