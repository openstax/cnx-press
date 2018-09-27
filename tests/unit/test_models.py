import hashlib
import io

from press.models import convert_litezip_resources

from tests.random_image import (
    generate_random_image_by_size,
    save_image,
)


def test_convert_litezip_resources(content_util):
    resources = []
    module = content_util.gen_module(resources=resources)

    # Generate some litezip compatible resourcess
    r1 = content_util.gen_resource()
    r2 = content_util.gen_resource()

    # Convert our test utilities Resource object to a path
    contextual_resources = []
    for r in [r1, r2]:
        filepath = module.file.parent / r.filename
        with filepath.open('wb') as fb:
            fb.write(r.data.read())
            r.data.seek(0)
            new_res = content_util.Resource(
                io.BytesIO(r.data.read()),
                r.filename,
                r.media_type,
                r.sha1,
            )
        contextual_resources.append(new_res)

    # Provide one resource as a Resource instance
    module.resources.append(contextual_resources[0])
    # Provide the other as a filepath
    module.resources.append(
        module.file.parent / contextual_resources[1].filename)

    r3_as_filepath = module.file.parent / 'test.jpeg'
    save_image(
        generate_random_image_by_size(10),
        str(r3_as_filepath),
    )
    module.resources.append(r3_as_filepath)

    # Bury the module in a collection structure
    collection, tree, modules = content_util.gen_collection(modules=[module])

    # TARGET
    struct = [collection]
    struct.extend(modules)
    struct = convert_litezip_resources(struct)

    # Flatten the collection to Modules and pick out our specific test module
    target_module = [
        model
        for model in struct
        if isinstance(model, content_util.Module) and model.id == module.id
    ][0]
    expected_resources = [
        r1,
        r2,
    ]
    with r3_as_filepath.open('rb') as fb:
        hash = hashlib.sha1()
        hash.update(fb.read())
        fb.seek(0)
        sha1 = hash.hexdigest()
        expected_resources.append(
            content_util.Resource(
                io.BytesIO(fb.read()),
                r3_as_filepath.name,
                'image/jpeg',
                sha1,
            )
        )

    def comparable_list(l):
        return list([[type(x[0])] + [tuple(x)[1:]] for x in l])

    expected_results = comparable_list(expected_resources)
    assert comparable_list(target_module.resources) == expected_results
